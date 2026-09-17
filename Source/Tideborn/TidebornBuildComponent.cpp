#include "TidebornBuildComponent.h"
#include "TidebornBuildPiece.h"
#include "TidebornInventoryComponent.h"
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

	IC->BindKey(EKeys::LeftMouseButton, IE_Pressed, this, &UTidebornBuildComponent::OnPlaceClick);
	IC->BindKey(EKeys::RightMouseButton, IE_Pressed, this, &UTidebornBuildComponent::OnCancelClick);
	UE_LOG(LogTemp, Log, TEXT("TidebornBuild: bound LMB place / RMB cancel"));
}

void UTidebornBuildComponent::OnPlaceClick()
{
	if (bPlaceMode)
	{
		TryCommitPlacement();
	}
}

void UTidebornBuildComponent::OnCancelClick()
{
	if (bPlaceMode)
	{
		CancelPlaceMode();
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(93001, 3.f, FColor::Magenta, TEXT("Place cancelled"));
		}
	}
}

FVector UTidebornBuildComponent::SnapPlaceLocation(const FVector& Raw) const
{
	FVector PlaceLoc = Raw;
	PlaceLoc.X = FMath::GridSnap(PlaceLoc.X, SnapSize);
	PlaceLoc.Y = FMath::GridSnap(PlaceLoc.Y, SnapSize);
	PlaceLoc.Z = Raw.Z + 15.f;
	return PlaceLoc;
}

void UTidebornBuildComponent::BeginPlaceMode(FName PieceId)
{
	RequiredItemId = PieceId.IsNone() ? FName(TEXT("Foundation")) : PieceId;
	bPlaceMode = true;

	UTidebornInventoryComponent* Inv = GetInventory();
	const int32 Have = Inv ? Inv->CountItem(RequiredItemId) : 0;
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(93001, 8.f, Have > 0 ? FColor::Magenta : FColor::Orange,
			FString::Printf(TEXT("Placing %s (owned %d). WASD+look, LMB place, RMB cancel."),
				*RequiredItemId.ToString(), Have));
	}
}

void UTidebornBuildComponent::CancelPlaceMode()
{
	bPlaceMode = false;
	if (GhostActor)
	{
		GhostActor->Destroy();
		GhostActor = nullptr;
	}
}

void UTidebornBuildComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	if (bPlaceMode)
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
	if (!bPlaceMode)
	{
		return false;
	}

	UTidebornInventoryComponent* Inv = GetInventory();
	if (!Inv || !Inv->RemoveItem(RequiredItemId, 1))
	{
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(93002, 8.f, FColor::Orange,
				TEXT("Need a Foundation item — open Inventory (I) and craft from 5 Wood."));
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
			GEngine->AddOnScreenDebugMessage(93002, 6.f, FColor::Magenta,
				FString::Printf(TEXT("Placed %s (%d left). LMB place another, RMB stop."), *RequiredItemId.ToString(), Left));
		}
	}
	else
	{
		Inv->AddItem(RequiredItemId, 1);
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
