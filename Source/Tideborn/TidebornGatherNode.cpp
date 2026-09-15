#include "TidebornGatherNode.h"
#include "TidebornInventoryComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/Engine.h"

ATidebornGatherNode::ATidebornGatherNode()
{
	PrimaryActorTick.bCanEverTick = false;

	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	RootComponent = Mesh;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeMesh.Succeeded())
	{
		Mesh->SetStaticMesh(CubeMesh.Object);
	}
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));
	Mesh->SetGenerateOverlapEvents(true);
	Mesh->SetCanEverAffectNavigation(false);
}

void ATidebornGatherNode::BeginPlay()
{
	Super::BeginPlay();

	// Tall bright pillar so it is not confused with level greybox
	SetActorScale3D(FVector(0.8f, 0.8f, 2.2f));

	if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial")))
	{
		UMaterialInstanceDynamic* Dyn = UMaterialInstanceDynamic::Create(Base, this);
		if (Dyn)
		{
			const FLinearColor Color = (ItemId == FName(TEXT("Stone")))
				? FLinearColor(0.55f, 0.55f, 0.6f)
				: FLinearColor(1.f, 0.45f, 0.05f);
			Dyn->SetVectorParameterValue(TEXT("Color"), Color);
			Mesh->SetMaterial(0, Dyn);
		}
	}
}

bool ATidebornGatherNode::Tideborn_TryInteract(AActor* Interactor)
{
	if (!Interactor || RemainingUses <= 0 || ItemId.IsNone())
	{
		return false;
	}

	UTidebornInventoryComponent* Inv = Interactor->FindComponentByClass<UTidebornInventoryComponent>();
	if (!Inv)
	{
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(-1, 3.f, FColor::Red, TEXT("Tideborn: NO inventory on character — reopen map / recompile"));
		}
		UE_LOG(LogTemp, Error, TEXT("TidebornGather: interactor has no UTidebornInventoryComponent"));
		return true;
	}

	if (!Inv->AddItem(ItemId, AmountPerGather))
	{
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(-1, 2.f, FColor::Red, TEXT("Tideborn: inventory full"));
		}
		return true;
	}

	--RemainingUses;
	const FString Msg = FString::Printf(TEXT("Tideborn Gathered %s x%d (left %d)"), *ItemId.ToString(), AmountPerGather, RemainingUses);
	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 2.5f, FColor::Green, Msg);
	}
	UE_LOG(LogTemp, Log, TEXT("%s"), *Msg);

	if (RemainingUses <= 0)
	{
		Destroy();
	}
	return true;
}

