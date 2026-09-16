#include "TidebornBuildComponent.h"
#include "TidebornInventoryComponent.h"
#include "TidebornCraftingComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
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
		// Point craft selection at Foundation so C makes the build piece
		if (UTidebornCraftingComponent* Craft = GetOwner()->FindComponentByClass<UTidebornCraftingComponent>())
		{
			Craft->SelectRecipeById(FName(TEXT("Foundation")));
		}

		if (GEngine)
		{
			if (Have > 0)
			{
				GEngine->AddOnScreenDebugMessage(-1, 4.f, FColor::Magenta,
					FString::Printf(TEXT("Build ON: placing %s (you have %d). Aim + E to place. B to cancel."),
						*RequiredItemId.ToString(), Have));
			}
			else
			{
				GEngine->AddOnScreenDebugMessage(-1, 5.f, FColor::Orange,
					TEXT("Build ON but you have 0 Foundation. Gather Wood, then C crafts Foundation (5 Wood). [ ] changes recipe."));
			}
		}
	}
	else if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 2.f, FColor::Magenta, TEXT("Build OFF"));
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

AActor* UTidebornBuildComponent::SpawnBuildPiece(const FTransform& Xform, bool bGhost)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AStaticMeshActor* Piece = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), Xform, Params);
	if (!Piece)
	{
		return nullptr;
	}

	UStaticMeshComponent* SMC = Piece->GetStaticMeshComponent();
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (Cube && SMC)
	{
		SMC->SetStaticMesh(Cube);
		SMC->SetWorldScale3D(FVector(1.f, 1.f, 0.2f));
	}

	if (bGhost && SMC)
	{
		SMC->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Piece->SetActorEnableCollision(false);
	}
	else if (SMC)
	{
		SMC->SetCollisionProfileName(TEXT("BlockAll"));
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
	GetWorld()->LineTraceSingleByChannel(Hit, CamLoc, End, ECC_Visibility, Params);

	FVector PlaceLoc = Hit.bBlockingHit ? Hit.ImpactPoint : (CamLoc + CamRot.Vector() * 200.f);
	PlaceLoc.X = FMath::GridSnap(PlaceLoc.X, SnapSize);
	PlaceLoc.Y = FMath::GridSnap(PlaceLoc.Y, SnapSize);
	PlaceLoc.Z = FMath::GridSnap(PlaceLoc.Z, SnapSize);
	GhostTransform = FTransform(FRotator::ZeroRotator, PlaceLoc);
	bGhostValid = true;

	if (!GhostActor)
	{
		GhostActor = SpawnBuildPiece(GhostTransform, true);
	}
	else
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
			GEngine->AddOnScreenDebugMessage(-1, 3.f, FColor::Orange,
				TEXT("Need a Foundation in inventory. Select Foundation with [ ], craft with C (5 Wood)."));
		}
		if (UTidebornCraftingComponent* Craft = GetOwner()->FindComponentByClass<UTidebornCraftingComponent>())
		{
			Craft->SelectRecipeById(FName(TEXT("Foundation")));
		}
		return true;
	}

	AActor* Placed = SpawnBuildPiece(GhostTransform, false);
	if (Placed)
	{
		PlacedActors.Add(Placed);
		const int32 Left = Inv->CountItem(RequiredItemId);
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(-1, 2.f, FColor::Magenta,
				FString::Printf(TEXT("Foundation placed (%d left)"), Left));
		}
	}
	return true;
}

TArray<FTransform> UTidebornBuildComponent::GetPlacedTransforms() const
{
	TArray<FTransform> Out;
	for (AActor* A : PlacedActors)
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
	for (AActor* A : PlacedActors)
	{
		if (IsValid(A))
		{
			A->Destroy();
		}
	}
	PlacedActors.Reset();
	for (const FTransform& X : Transforms)
	{
		if (AActor* A = SpawnBuildPiece(X, false))
		{
			PlacedActors.Add(A);
		}
	}
}
