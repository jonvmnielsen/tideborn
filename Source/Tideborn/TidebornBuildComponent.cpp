#include "TidebornBuildComponent.h"
#include "TidebornBuildPiece.h"
#include "TidebornInventoryComponent.h"
#include "TidebornCraftingComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Components/InputComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "CollisionQueryParams.h"
#include "TimerManager.h"

UTidebornBuildComponent::UTidebornBuildComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UTidebornBuildComponent::BeginPlay()
{
	Super::BeginPlay();
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(this, &UTidebornBuildComponent::BindHotkeys));
	}
}

void UTidebornBuildComponent::BindHotkeys()
{
	APawn* Pawn = Cast<APawn>(GetOwner());
	APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!PC && GetWorld())
	{
		PC = GetWorld()->GetFirstPlayerController();
	}

	UInputComponent* IC = Pawn ? Pawn->InputComponent : nullptr;
	if (!IC && PC)
	{
		IC = PC->InputComponent;
	}
	if (!IC)
	{
		if (UWorld* World = GetWorld())
		{
			FTimerHandle Handle;
			World->GetTimerManager().SetTimer(Handle, this, &UTidebornBuildComponent::BindHotkeys, 0.25f, false);
		}
		return;
	}

	IC->BindKey(EKeys::B, IE_Pressed, this, &UTidebornBuildComponent::OnToggleBuildKey);
	UE_LOG(LogTemp, Log, TEXT("TidebornBuild: bound B"));
}

void UTidebornBuildComponent::OnToggleBuildKey()
{
	ToggleBuildMode();
}

FVector UTidebornBuildComponent::SnapPlaceLocation(const FVector& Raw) const
{
	FVector PlaceLoc = Raw;
	PlaceLoc.X = FMath::GridSnap(PlaceLoc.X, SnapSize);
	PlaceLoc.Y = FMath::GridSnap(PlaceLoc.Y, SnapSize);
	// Keep Z near the hit surface, then lift so the slab sits on top (cube*0.25 scale => ~12.5uu half-height on 100uu mesh... scale Z 0.25 => 25uu tall, half = 12.5)
	PlaceLoc.Z = Raw.Z + 15.f;
	return PlaceLoc;
}

void UTidebornBuildComponent::ToggleBuildMode()
{
	bBuildMode = !bBuildMode;
	if (!bBuildMode && GhostActor)
	{
		GhostActor->Destroy();
		GhostActor = nullptr;
	}

	UTidebornInventoryComponent* Inv = GetInventory();
	const int32 Have = Inv ? Inv->CountItem(RequiredItemId) : 0;

	if (bBuildMode)
	{
		if (UTidebornCraftingComponent* Craft = GetOwner()->FindComponentByClass<UTidebornCraftingComponent>())
		{
			Craft->SelectRecipeById(FName(TEXT("Foundation")));
		}

		if (GEngine)
		{
			if (Have > 0)
			{
				GEngine->AddOnScreenDebugMessage(93001, 12.f, FColor::Magenta,
					FString::Printf(TEXT("Build ON: %s x%d — aim at ground, E to place, B cancel"), *RequiredItemId.ToString(), Have));
			}
			else
			{
				GEngine->AddOnScreenDebugMessage(93001, 12.f, FColor::Orange,
					TEXT("Build ON — 0 Foundation. Scroll to Foundation, C craft (5 Wood), then E to place."));
			}
		}
	}
	else if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(93001, 3.f, FColor::Magenta, TEXT("Build OFF"));
	}
}

void UTidebornBuildComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	if (bBuildMode)
	{
		UpdateGhost();
	}
}

UTidebornInventoryComponent* UTidebornBuildComponent::GetInventory() const
{
	return GetOwner() ? GetOwner()->FindComponentByClass<UTidebornInventoryComponent>() : nullptr;
}

ATidebornBuildPiece* UTidebornBuildComponent::SpawnBuildPiece(const FTransform& Xform, bool bGhost)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ATidebornBuildPiece* Piece = World->SpawnActor<ATidebornBuildPiece>(ATidebornBuildPiece::StaticClass(), Xform, Params);
	if (!Piece)
	{
		UE_LOG(LogTemp, Error, TEXT("TidebornBuild: SpawnBuildPiece failed"));
		return nullptr;
	}

	if (bGhost)
	{
		Piece->ConfigureAsGhost();
	}
	else
	{
		Piece->ConfigureAsPlaced();
	}
	return Piece;
}

void UTidebornBuildComponent::UpdateGhost()
{
	APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!PC)
	{
		return;
	}

	FVector CamLoc;
	FRotator CamRot;
	PC->GetPlayerViewPoint(CamLoc, CamRot);
	const FVector End = CamLoc + CamRot.Vector() * PlaceDistance;

	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(TidebornBuild), false, GetOwner());
	if (GhostActor)
	{
		Params.AddIgnoredActor(GhostActor);
	}
	for (ATidebornBuildPiece* P : PlacedActors)
	{
		if (IsValid(P))
		{
			Params.AddIgnoredActor(P);
		}
	}

	bool bHit = GetWorld()->LineTraceSingleByChannel(Hit, CamLoc, End, ECC_Visibility, Params);
	if (!bHit)
	{
		bHit = GetWorld()->LineTraceSingleByChannel(Hit, CamLoc, End, ECC_WorldStatic, Params);
	}

	const FVector Raw = bHit ? Hit.ImpactPoint : (CamLoc + CamRot.Vector() * 250.f);
	GhostTransform = FTransform(FRotator::ZeroRotator, SnapPlaceLocation(Raw));
	bGhostValid = true;

	if (!GhostActor)
	{
		GhostActor = SpawnBuildPiece(GhostTransform, true);
	}
	if (GhostActor)
	{
		GhostActor->SetActorTransform(GhostTransform);
	}
}

bool UTidebornBuildComponent::TryCommitPlacement()
{
	if (!bBuildMode)
	{
		return false;
	}

	UTidebornInventoryComponent* Inv = GetInventory();
	if (!Inv || !Inv->RemoveItem(RequiredItemId, 1))
	{
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(93002, 10.f, FColor::Orange,
				TEXT("Need Foundation. Scroll recipes, C to craft (5 Wood)."));
		}
		if (UTidebornCraftingComponent* Craft = GetOwner()->FindComponentByClass<UTidebornCraftingComponent>())
		{
			Craft->SelectRecipeById(FName(TEXT("Foundation")));
		}
		return true;
	}

	ATidebornBuildPiece* Placed = SpawnBuildPiece(GhostTransform, false);
	if (Placed)
	{
		PlacedActors.Add(Placed);
		const int32 Left = Inv->CountItem(RequiredItemId);
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(93002, 8.f, FColor::Magenta,
				FString::Printf(TEXT("Foundation placed at %s (%d left)"), *GhostTransform.GetLocation().ToCompactString(), Left));
		}
		UE_LOG(LogTemp, Log, TEXT("TidebornBuild: placed foundation at %s"), *GhostTransform.GetLocation().ToString());
	}
	else if (GEngine)
	{
		// refund
		Inv->AddItem(RequiredItemId, 1);
		GEngine->AddOnScreenDebugMessage(93002, 8.f, FColor::Red, TEXT("Foundation spawn failed — item refunded"));
	}
	return true;
}

TArray<FTransform> UTidebornBuildComponent::GetPlacedTransforms() const
{
	TArray<FTransform> Out;
	for (ATidebornBuildPiece* A : PlacedActors)
	{
		if (IsValid(A))
		{
			Out.Add(A->GetActorTransform());
		}
	}
	return Out;
}

void UTidebornBuildComponent::RestorePlaced(const TArray<FTransform>& Transforms)
{
	for (ATidebornBuildPiece* A : PlacedActors)
	{
		if (IsValid(A))
		{
			A->Destroy();
		}
	}
	PlacedActors.Reset();
	for (const FTransform& X : Transforms)
	{
		if (ATidebornBuildPiece* A = SpawnBuildPiece(X, false))
		{
			PlacedActors.Add(A);
		}
	}
}
